from app.topic.repositories import TopicRepository
from app.topic.services import TopicService


def get_topic_service() -> TopicService:
    topic_repo = TopicRepository()
    return TopicService(topic_repo)
