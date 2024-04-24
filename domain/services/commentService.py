from domain.models.userModels import Comments


class CommentService:
    def __init__(self, comment_repository):
        self.comment_repository = comment_repository

    def post_comment(self, user_id, food_id, content, parent_comment_id=None):
        comment = Comments(comment_id=None, user_id=user_id, food_id=food_id, content=content, parent_comment_id=parent_comment_id, has_child=False)
        self.comment_repository.save(comment)
        return comment

    def get_comments_for_food(self, food_id):
        return self.comment_repository.find_by_food_id(food_id)

    def get_comments_for_user(self, user_id):
        return self.comment_repository.find_by_user_id(user_id)
    
    def get_comment_by_id(self, comment_id):
        return self.comment_repository.find_by_id(comment_id)
    
    def delete_comment(self, comment_id):
        comment = self.get_comment_by_id(comment_id)
        if not comment:
            raise ValueError("Comment not found")
        self.comment_repository.delete(comment_id)
        return True
    
    def update_comment(self, comment_id, content):
        comment = self.get_comment_by_id(comment_id)
        if not comment:
            raise ValueError("Comment not found")
        comment.content = content
        self.comment_repository.save(comment)
        return comment