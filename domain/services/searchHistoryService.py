from domain.models.userModels import SearchHistory


class SearchHistoryService:
    def __init__(self, search_history_repository):
        self.search_history_repository = search_history_repository

    def log_search(self, user_id, query):
        search_history = SearchHistory(user_id=user_id, query=query)
        self.search_history_repository.save(search_history)
        return search_history
    
    def get_all_search_history(self):
        return self.search_history_repository.find_all()
    
    def get_search_history_by_user_id(self, user_id):
        return self.search_history_repository.find_all_by_user_id(user_id)

    def delete_search_history_by_user_id(self, user_id):
        return self.search_history_repository.delete_by_user_id(user_id)
    
    def delete_search_history_by_id(self, id):
        return self.search_history_repository.delete_by_id(id)

    def set_search_history_by_user_id(self, user_id, search_history):
        return self.search_history_repository.update_by_user_id(user_id, search_history)