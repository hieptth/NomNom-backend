from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import faiss
import numpy as np
import pandas as pd

class SearchModel:
    def __init__(self, nutritions_scaler=None):
        self.data = {}
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.index_for_name = None # Index is the model by faiss
        self.index_for_tags = None
        self.index_for_ingredients = None
        self.index_for_nutrition = None
        self.scaler = nutritions_scaler

    def embed(self, sentences):
        '''
            sentences: list of strings
            return: list of embeddings
        '''
        return self.embedding_model.encode(sentences)

    def fit_name(self, embeddings):
        self.index_for_name = faiss.IndexFlatIP(embeddings.shape[1])  # IndexFlatIP for inner product (cosine similarity)
        self.index_for_name.add(embeddings)

    def fit_tag(self, embeddings):
        self.index_for_tags = faiss.IndexFlatIP(embeddings.shape[1])  # IndexFlatIP for inner product (cosine similarity)
        self.index_for_tags.add(embeddings)

    def fit_ingredients(self, embeddings):
        self.index_for_ingredients = faiss.IndexFlatIP(embeddings.shape[1])  # IndexFlatIP for inner product (cosine similarity)
        self.index_for_ingredients.add(embeddings)

    def fit_nutrition(self, nutrition):
        nutrition = np.ascontiguousarray(nutrition, dtype=np.float32)
        self.index_for_nutrition = faiss.IndexFlatL2(7)  # IndexFlatL1 for L1 distance (Manhattan)
        self.index_for_nutrition.add(nutrition)

    def fit(self, embedded_names, embedded_tags, embedded_ingredients, nutritions_scaled):
        self.fit_name(embedded_names)
        self.fit_tag(embedded_tags)
        self.fit_ingredients(embedded_ingredients)
        self.fit_nutrition(nutritions_scaled)

    def load(self, data):
        '''
            data: dataframe
        '''
        print('[+] Loading data into model...')
        self.data = data

    def search(self, name: str=None, tags: str=None, ingredients: str=None, nutrition: list[float]=None, k=1000):
        '''
            return: list of similar
        '''
        print('[+] Retrieving similar foods...')
        final_res = {}
        name_indices = tags_indices = ingredients_indices = nutrition_indices = [[]]
        if name:
            embedded_name = self.embedding_model.encode(name)
            name_scores, name_indices = self.index_for_name.search(embedded_name.reshape(1, -1), k=k)
            for i, idx in enumerate(name_indices[0]):
                if idx not in final_res:
                    final_res[idx] = {}
                final_res[idx]['name'] = name_scores[0][i]

        if tags:
            embedded_tags = self.embedding_model.encode(tags)
            tags_scores, tags_indices = self.index_for_tags.search(embedded_tags.reshape(1, -1), k=k)
            for i, idx in enumerate(tags_indices[0]):
                if idx not in final_res:
                    final_res[idx] = {}
                final_res[idx]['tags'] = tags_scores[0][i]

        if ingredients:
            embedded_ingredients = self.embedding_model.encode(ingredients)
            ingredients_scores, ingredients_indices = self.index_for_ingredients.search(embedded_ingredients.reshape(1, -1), k=k)
            for i, idx in enumerate(ingredients_indices[0]):
                if idx not in final_res:
                    final_res[idx] = {}
                final_res[idx]['ingredients'] = ingredients_scores[0][i]

        if nutrition:
            scaled_nutrition = np.array(nutrition).reshape(1, -1)
            scaled_nutrition = self.scaler.transform(scaled_nutrition)
            nutrition_scores, nutrition_indices = self.index_for_nutrition.search(scaled_nutrition.reshape(1, -1), k=k)
            max_nutrition_scores = max(nutrition_scores[0])
            normalized_nutrition_scores = [1 - score/max_nutrition_scores for score in nutrition_scores[0]]
            for i, idx in enumerate(nutrition_indices[0]):
                if idx not in final_res:
                    final_res[idx] = {}
                final_res[idx]['nutrition'] = normalized_nutrition_scores[i]

        final_list = [
            (idx, sum([score for crit, score in scores.items()])) for idx, scores in final_res.items()
        ]
        print(len(final_list))

        return [(self.data.iloc[idx], score) for idx, score in sorted(final_list, key=lambda x: x[1], reverse=True)]
