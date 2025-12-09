import subprocess
import time
import requests
import os
from requests.exceptions import ConnectionError

from pymilvus import connections
from pymilvus.exceptions import MilvusException

IS_CI = os.getenv("CI", "false").lower() == "true"

SERVICES_TO_WAIT_FOR = ["milvus-standalone", "elasticsearch", "kafka"]


def wait_for_elasticsearch_ready(host="elasticsearch", port=9200, timeout=120):
    print("⏳ Waiting for Elasticsearch to be ready...")
    start_time = time.time()
    url = f"http://{host}:{port}/_cluster/health"
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                health = response.json()
                if health["status"] in ("yellow", "green"):
                    print("✅ Elasticsearch is ready.")
                    return
                print(f"🔁 Elasticsearch status: {health['status']}... waiting")
        except ConnectionError:
            print("🔁 Elasticsearch not responding yet...")
        time.sleep(5)
    
    raise TimeoutError("❌ Timeout waiting for Elasticsearch to become ready.")


def wait_for_milvus_ready(host="localhost", port="19530", timeout=120):
    print("⏳ Waiting for Milvus to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            connections.connect(host=host, port=port)
            print("✅ Milvus is ready.")
            return
        except MilvusException as e:
            if "service not ready" in str(e).lower():
                print("🔁 Milvus initializing... retrying.")
            else:
                print(f"⚠️ Unexpected Milvus error: {e}")
                raise
        time.sleep(5)
    raise TimeoutError("❌ Timeout waiting for Milvus to become ready.")


def wait_for_services(timeout=120):
    print("⏳ Waiting for required containers to be running...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            text=True
        )
        running = result.stdout.strip().splitlines()
        if all(any(s in name for name in running) for s in SERVICES_TO_WAIT_FOR):
            print("✅ All required containers are running.")
            return
        print("🔁 Still waiting for services to be ready...")
        time.sleep(5)
    raise TimeoutError("❌ Timeout waiting for containers to run.")


def wait_for_http_service(url, timeout=60):
    print(f"⏳ Waiting for {url} to be reachable...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"✅ {url} is ready.")
                return
        except Exception:
            pass
        time.sleep(5)
    raise TimeoutError(f"❌ Timeout waiting for {url}")


def run(command, cwd=None, background=False):
    print(f"▶ Running: {command}")
    if background:
        return subprocess.Popen(command, shell=True, cwd=cwd)
    else:
        subprocess.run(command, shell=True, cwd=cwd, check=True)


def run_in_new_terminal(command_str):
    if IS_CI:
        print(f"ℹ️ Skipping terminal startup in CI: {command_str}")
    else:
        subprocess.Popen(f'start cmd /k {command_str}', shell=True)


def main():
    if not IS_CI:
        run("docker compose up -d")
        wait_for_services(timeout=180)

    wait_for_milvus_ready()
    run("python -m backend.milvus.setup")

    wait_for_elasticsearch_ready()
    run("python -m backend.utils.elastic_search.es_client")

    if IS_CI:
        run("python -m backend.embedding.consumer", background=True)
        run("python -m backend.embedding.producer", background=True)
        run("python -m backend.embedding.query_consumer", background=True)
        run("python -m backend.embedding.query_producer", background=True)
        run("uvicorn backend.api.main:app --host 0.0.0.0 --port 8001", background=True)
        run("streamlit run frontend/app.py", background=True)

        wait_for_http_service("http://localhost:8001/docs")
        wait_for_http_service("http://localhost:8501")
    else:
        run_in_new_terminal("python -m backend.embedding.consumer")
        run_in_new_terminal("python -m backend.embedding.producer")
        run_in_new_terminal("python -m backend.embedding.query_consumer")
        run_in_new_terminal("python -m backend.embedding.query_producer")
        run_in_new_terminal("uvicorn backend.api.main:app --host 0.0.0.0 --port 8001")
        run_in_new_terminal("streamlit run frontend/app.py")

    print("🎉 ✅ All services started.")


if __name__ == "__main__":
    main()
