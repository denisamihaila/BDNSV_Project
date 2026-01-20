import requests
import time
import random
import matplotlib.pyplot as plt
import numpy as np

API_URL = "http://127.0.0.1:8000/products"
NUM_REQUESTS = 1000

def measure_request(method, url, params=None):
    start = time.time()
    try:
        if method == 'GET':
            requests.get(url, params=params)
        elif method == 'PUT':
            requests.put(url, params=params) 
        elif method == 'POST':
            requests.post(url, params=params)
    except Exception as e:
        print(f"Eroare: {e}")
    end = time.time()
    return (end - start) * 1000

def run_test_suite(scenario_name, use_delay, current_ids):
    print(f"\nPornim Scenariul: {scenario_name}...")
    
    results = {
        "read_miss": [],
        "read_hit": [],
        "write_through": [],
        "write_behind": []
    }

    delay_str = 'true' if use_delay else 'false'
    read_params = {"simulate_delay": delay_str}

    # TESTE DE CITIRE (CACHE-ASIDE)
    print("Testam Strategia CACHE-ASIDE...")
    for pid in current_ids:
        url = f"{API_URL}/{pid}"
        
        t_miss = measure_request('GET', url, params=read_params)
        results["read_miss"].append(t_miss)
        
        t_hit = measure_request('GET', url, params=read_params)
        results["read_hit"].append(t_hit)

    # TESTE DE SCRIERE
    print("Testam Strategiile de SCRIERE...")
    for pid in current_ids:
        # Write-Through (Update Price)
        url_put = f"{API_URL}/{pid}/price"
        
        put_params = {"new_price": 99.99, "simulate_delay": delay_str}
        
        t_wt = measure_request('PUT', url_put, params=put_params)
        results["write_through"].append(t_wt)

        # Write-Behind (Add View)
        url_post = f"{API_URL}/{pid}/view"
        t_wb = measure_request('POST', url_post)
        results["write_behind"].append(t_wb)

    return results

def generate_dashboard(results, title, filename):
    avg_miss = np.mean(results["read_miss"])
    avg_hit = np.mean(results["read_hit"])
    avg_wt = np.mean(results["write_through"])
    avg_wb = np.mean(results["write_behind"])

    print(f"\nREZULTATE {title}:")
    print(f"- Read Mongo (Miss): {avg_miss:.2f} ms")
    print(f"- Read Redis (Hit): {avg_hit:.2f} ms")
    print(f"- Write-Through: {avg_wt:.2f} ms")
    print(f"- Write-Behind: {avg_wb:.2f} ms")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f'Benchmark: {title}', fontsize=16)

    # GRAFIC 1: CITIRE
    labels_read = ['Cache MISS\n(MongoDB)', 'Cache HIT\n(Redis)']
    values_read = [avg_miss, avg_hit]
    colors_read = ["#a71515", "#19cf31"]

    bars1 = ax1.bar(labels_read, values_read, color=colors_read, alpha=0.7)
    ax1.set_title('Strategia 1: Cache-Aside (Citire)')
    ax1.set_ylabel('Timp de Raspuns (ms)')
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, yval + (yval*0.01) + 0.1, f"{yval:.2f} ms", ha='center', fontweight='bold')

    # GRAFIC 2: SCRIERE
    labels_write = ['Write-Through', 'Write-Behind']
    values_write = [avg_wt, avg_wb]
    colors_write = ["#f35912", "#2feed4"]

    bars2 = ax2.bar(labels_write, values_write, color=colors_write, alpha=0.7)
    ax2.set_title('Strategia 2 vs 3: Metode de Scriere')
    ax2.set_ylabel('Timp de Raspuns (ms)')
    ax2.grid(axis='y', linestyle='--', alpha=0.5)

    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, yval + (yval*0.01) + 0.1, f"{yval:.2f} ms", ha='center', fontweight='bold')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(filename)
    print(f"    Graficul a fost salvat ca: {filename}")

if __name__ == "__main__":
    # ---------------------------------------------------------
    # LOCALHOST (FARA DELAY)
    # Folosim ID-uri din prima jumatate (1 - 5000)
    # ---------------------------------------------------------
    IDS_LOCAL = [random.randint(1, 5000) for _ in range(NUM_REQUESTS)]
    
    data_local = run_test_suite("Localhost", False, IDS_LOCAL)
    generate_dashboard(data_local, "Infrastructura Locala", "benchmark_local.png")

    # ---------------------------------------------------------
    # Simularea CLOUD-ului (cu Delay 50ms)
    # Folosim ID-uri din a doua jumatate (5001 - 10000), pentru a fi siguri ca exista in DB, dar nu si in Redis.
    # ---------------------------------------------------------
    IDS_CLOUD = [random.randint(5001, 10000) for _ in range(NUM_REQUESTS)]
    
    data_cloud = run_test_suite("Cloud Simulation", True, IDS_CLOUD)
    generate_dashboard(data_cloud, "Simulare Cloud", "benchmark_cloud.png")