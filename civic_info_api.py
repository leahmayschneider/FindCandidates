import requests
import pandas as pd
from mappings import state_abbreviation_map  # Import state abbreviation map


class CivicInfoAPI:

    def __init__(self):
        self.api_key = "AIzaSyATdkdTDAaIa0yfUIyVlLj799KwhCnWIDE"

    def fetch_data(self, address):
        api_endpoint = "https://www.googleapis.com/civicinfo/v2/representatives"
        params = {"address": address, "key": self.api_key}
        response = requests.get(api_endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            state = data['normalizedInput']['state'].upper(
            )  # Extract the normalized state
            return self._process_data(data), state
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def _process_data(self, data):
        divisions_list = []
        offices_list = []
        officials_list = []

        # Process divisions
        for division_id, division_info in data['divisions'].items():
            division_name = division_info.get('name', '')
            also_known_as = ", ".join(division_info.get('alsoKnownAs', []))
            office_indices = division_info.get('officeIndices', [])
            for office_index in office_indices:
                divisions_list.append({
                    'Division ID': division_id,
                    'Division Name': division_name,
                    'Office Index': office_index
                })

        # Process offices
        for office_index, office_info in enumerate(data['offices']):
            office_name = office_info.get('name', '')
            division_id = office_info.get('divisionId', '')
            levels = ", ".join(office_info.get('levels', []))
            roles = ", ".join(office_info.get('roles', []))
            sources = ", ".join(
                [source['name'] for source in office_info.get('sources', [])])
            official_indices = office_info.get('officialIndices', [])
            for official_index in official_indices:
                offices_list.append({
                    'Office Index': office_index,
                    'Office Name': office_name,
                    'Division ID': division_id,
                    'Levels': levels,
                    'Roles': roles,
                    'Sources': sources,
                    'Official Index': official_index
                })

        # Process officials
        for official_index, official_info in enumerate(data['officials']):
            official_name = official_info.get('name', '')
            party = official_info.get('party', '')
            for address in official_info.get('address', []):
                officials_list.append({
                    'Official Index': official_index,
                    'Official Name': official_name,
                    'Party': party
                })

        df_divisions = pd.DataFrame(divisions_list)
        df_offices = pd.DataFrame(offices_list)
        df_officials = pd.DataFrame(officials_list)

        df = pd.merge(df_divisions, df_offices, on='Office Index', how='outer')
        df = pd.merge(df, df_officials, on='Official Index', how='outer')

        return df
