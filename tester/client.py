import requests
import time

class APIClient:
    def __init__(self, base_url):
        # C'est l'adresse principale de notre API (ex: l'adresse du restaurant)
        self.base_url = base_url

    def request(self, endpoint):
        # On colle l'adresse principale avec la suite (ex: /anime/11061)
        url = f"{self.base_url}{endpoint}"
        max_retries = 1  # On s'autorise à réessayer 1 seule fois (Robustesse)
        
        for attempt in range(max_retries + 1):
            start_time = time.time()  # On lance le chronomètre ⏱️
            
            try:
                # On fait la requête avec un "timeout" de 3 secondes max
                response = requests.get(url, timeout=3)
                
                # On arrête le chrono et on calcule le temps en millisecondes
                latency = (time.time() - start_time) * 1000 
                
                # Si le serveur dit "Je suis surchargé" (429) ou "J'ai un bug" (5xx)
                if response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < max_retries:
                        print(f"Erreur {response.status_code}. On patiente 2s et on réessaie...")
                        time.sleep(2)  # On attend 2 secondes avant la 2ème tentative
                        continue  # On relance la boucle pour réessayer
                
                # Si le code est 200 (OK) ou 404 (Introuvable, ce qui est normal si on le teste exprès), on renvoie le résultat
                return response, latency
                
            except requests.exceptions.RequestException as e:
                # Si l'API ne répond pas du tout (Coupure internet, Timeout dépassé...)
                if attempt < max_retries:
                    print(f"L'API ne répond pas. On retente dans 2s...")
                    time.sleep(2)
                    continue
                
                # Si ça rate même après la deuxième tentative, on renvoie "None" (Rien)
                latency = (time.time() - start_time) * 1000
                return None, latency
