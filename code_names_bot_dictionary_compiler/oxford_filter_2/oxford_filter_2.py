from code_names_bot_dictionary_compiler.download.caches import OxfordDefinitionsCache, OxfordSentencesCache

from config import OXFORD_FILTERED_1, OXFORD_FILTERED_2, MISSING_SENTENCES

import json
import yaml
from collections import defaultdict

def get_sense_sentence_counts(lemmas):
    sentences_cache = OxfordSentencesCache()
    query_to_result = sentences_cache.get_key_to_value()
    sentence_counts = defaultdict(lambda: 0)

    for lemma in lemmas:
        results_str = query_to_result[lemma]
        results = json.loads(results_str)
        for result in results["results"]:
            for lexical_entry in result["lexicalEntries"]:
                for sentence in lexical_entry["sentences"]:
                    for sense_id in set(sentence["senseIds"]):
                        sentence_counts[sense_id] += 1
    
    return sentence_counts


def extract_sense_data(sense_json):
    sense_id = sense_json["id"]
    definition = sense_json["definitions"][0]
    synonyms, domains = []

    if "domainClasses" in sense_json:
        domains = [ domain_class["id"] for domain_class in sense_json["domainClasses"] ]

    if "synonyms" in sense_json:
        synonyms = [ synonym["text"] for synonym in sense_json["synonyms"] ]
    
    return sense_id, definition, synonyms, domains


def get_sense_definitions(lemmas):
    definitions_cache = OxfordDefinitionsCache()
    definitions = dict()
    query_to_result = definitions_cache.get_key_to_value()
    
    for lemma in lemmas:
        results_str = query_to_result[lemma]
        results = json.loads(results_str)
        for result in results["results"]:
            for lexical_entry in result["lexicalEntries"]:
                text = lexical_entry["text"]
                lexical_category = lexical_entry["lexicalCategory"]["id"]

                for entry in lexical_entry["entries"]:
                    grammatical_features, inflections = []
                    if "grammaticalFeatures" in entry:
                        grammatical_features = set([ grammatical_feature["id"] for grammatical_feature in entry["grammaticalFeatures"]])
                    if "inflections" in inflections:
                        inflections = set([ inflection["inflectedForm"] for inflection in entry["inflections"] ])

                    pos = "proper" if "proper" in grammatical_features else lexical_category

                    for sense in entry["senses"]:
                        sense_id, definition, synonyms, domains = extract_sense_data(sense)

                        definitions[sense_id] = {
                            "text": text,
                            "pos": pos,
                            "definition": definition,
                            "synonyms": synonyms,
                            "variants": inflections,
                            "domains": domains
                        }

                        if "subsenses" in sense:
                            for subsense in sense["subsenses"]:
                                subsense_id, definition, synonyms, domains = extract_sense_data(subsense)
                                definitions[subsense_id] = {
                                    "text": text,
                                    "pos": pos,
                                    "definition": definition,
                                    "synonyms": synonyms,
                                    "variants": inflections,
                                    "domains": domains
                                }
    return definitions


def main():
    with open(OXFORD_FILTERED_1, "r") as file:
        lemma_regions = file.read().splitlines()
        lemmas = map(lambda lemma_region: lemma_region.split("|")[0], lemma_regions)

    with open(MISSING_SENTENCES) as file:
        missing_sentences = set(file.read().splitlines())

    lemmas = list(filter(lambda lemma: lemma not in missing_sentences))

    sentence_counts = get_sense_sentence_counts(lemmas)
    definitions = get_sense_definitions(lemmas)

    sense_ids = definitions.keys()
    sense_ids = filter(lambda sense_id: definitions[sense_id]["pos"] == "proper" or sentence_counts[sense_id] > 0)

    filtered_definitions = { sense_id: definitions[sense_id] for sense_id in sense_ids }

    with open(OXFORD_FILTERED_2, "w+") as file:
        file.write(yaml.dump(filtered_definitions, sort_keys=True, default_flow_style=None))


if __name__ == "__main__":
    main()