from app.helpers import redis_utils


def trigger(new_submit_id):
    if new_submit_id:
        redis_utils.push_submit_to_queue(new_submit_id)
