import logging
from typing import List
import requests
from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_api_gateway import StoreGateway


class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]) -> bool:
        if not processed_agent_data_batch:
            return False

        url = f"{self.api_base_url}/processed_agent_data/"

        payload = [item.model_dump(mode='json') for item in processed_agent_data_batch]

        try:
            response = requests.post(url, json=payload)
            if response.status_code in (200, 201):
                logging.info(f"Успішно збережено {len(processed_agent_data_batch)} записів у Store API.")
                return True
            else:
                logging.error(f"Помилка: {response.status_code}, Відповідь: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Помилка з'єднання: {e}")
            return False