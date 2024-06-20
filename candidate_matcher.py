import pandas as pd
from fuzzywuzzy import process
import re
from mappings import term_mapping, state_abbreviation_map, clean_text
import io


class CandidateMatcher:

    def __init__(self, endorsed_candidates_path):
        self.endorsed_candidates = self.load_endorsed_candidates(
            endorsed_candidates_path)
        self.output = io.StringIO()  # Capture print statements

    def load_endorsed_candidates(self, file_path):
        endorsed_candidates_df = pd.read_excel(file_path)
        endorsed_candidates_df['state'] = endorsed_candidates_df['state'].map(
            lambda x: state_abbreviation_map.get(x.upper(), x))
        endorsed_candidates_df['district_number'] = endorsed_candidates_df[
            'position'].apply(self.extract_district_number)
        endorsed_candidates_df['clean_position'] = endorsed_candidates_df[
            'position'].apply(self.standardize_and_clean)
        return endorsed_candidates_df

    def standardize_and_clean(self, term):
        term = term.lower()
        for key, value in term_mapping.items():
            term = term.replace(key.lower(), value)
        term = clean_text(term)
        return term.title()

    def extract_district_number(self, text):
        match = re.search(r'(\d+)', text)
        return match.group(1) if match else None

    def is_endorsed(self, division_name, office_name,
                    endorsed_candidates_state_df):
        # Extract and remove district numbers
        division_district_number = self.extract_district_number(division_name)
        office_district_number = self.extract_district_number(office_name)

        # Clean and standardize the names
        division_name_clean = clean_text(division_name)
        office_name_clean = clean_text(office_name)

        # Standardize office name using mapping
        office_name_standard = self.standardize_and_clean(office_name_clean)

        # Combine standardized values
        combined_office = f"{division_district_number}, {office_name_standard}"

        for _, row in endorsed_candidates_state_df.iterrows():
            original_candidate_position = row['position']
            candidate_position_clean = row['clean_position']
            candidate_district_number = row['district_number']

            if candidate_district_number and division_district_number:
                if candidate_district_number == division_district_number:
                    position_match_score = process.extractOne(
                        candidate_position_clean, [office_name_standard])[1]
                    if position_match_score > 90:
                        print(
                            f"In your district, WFP endorses {row['name']} running for {original_candidate_position} ",
                            file=self.output)
                        return True
            elif not candidate_district_number and not division_district_number:
                position_match_score = process.extractOne(
                    candidate_position_clean, [office_name_standard])[1]
                if position_match_score > 90:
                    print(
                        f"In your district, WFP endorses {row['name']} running for {original_candidate_position}",
                        file=self.output)
                    return True
        return False

    def mark_endorsed_candidates(self, api_df, normalized_state):
        # Filter endorsed candidates by normalized state
        endorsed_candidates_state_df = self.endorsed_candidates[
            self.endorsed_candidates['state'].str.lower() ==
            normalized_state.lower()]

        # Ensure necessary columns are of correct type
        api_df.loc[:, 'Division Name'] = api_df['Division Name'].astype(str)
        api_df.loc[:, 'Office Name'] = api_df['Office Name'].astype(str)

        # Apply endorsement check
        api_df.loc[:, 'Is Endorsed'] = api_df.apply(
            lambda x: self.is_endorsed(x['Division Name'], x['Office Name'],
                                       endorsed_candidates_state_df),
            axis=1)
        return api_df

    def get_output(self):
        return self.output.getvalue()
