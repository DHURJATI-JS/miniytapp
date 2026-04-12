import random
import resource
from locust import task, between
from locust.contrib.fasthttp import FastHttpUser

try:
    resource.setrlimit(resource.RLIMIT_NOFILE, (100000, 100000))
except Exception:
    pass

class WebsiteSpammer(FastHttpUser):
    wait_time = between(0.2, 0.5)

    connection_timeout = 60.0
    network_timeout = 60.0

    @task(5)
    def spam_homepage(self):
        self.client.get("/", name="Home Page")

    @task(5)
    def spam_channels(self):
        c_id = 1
        self.client.get(f"/channel/{c_id}", name="/channel/[id]")

    @task(3) 
    def spam_video_pages(self):
        v_id = 1
        self.client.get(f"/view_video/{v_id}", name="/view_video/[id]")

    @task(2)
    def spam_settings(self):
        self.client.get("/settings", name="/settings")    

    @task(3)
    def spam_community(self):
        self.client.get("/community", name="/community") 
  