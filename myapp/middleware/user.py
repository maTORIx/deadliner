from myapp.models import UUID, User
import json

class UserInfo(object):

    def process_request(self, request):
        print("management of request")
        uuid_cookie = request.COOKIES.get("user_session")
        uuid = UUID.objects.filter(uuid=uuid_cookie)
        if (len(uuid)):
          request.session["user_id"] = uuid[0].user_id
        else:
          request.session["user_id"] = None
        return None
    