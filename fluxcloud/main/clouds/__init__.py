from .aws import AmazonCloud
from .google import GoogleCloud
from .local import MiniKube

# backends = {"aws": AmazonCloud}
clouds = {
    "google": GoogleCloud,
    "gcp": GoogleCloud,
    "aws": AmazonCloud,
    "minikube": MiniKube,
}
cloud_names = list(clouds)


def get_cloud(name):
    return clouds.get(name)
