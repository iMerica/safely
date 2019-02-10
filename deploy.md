# Deploy Options for Safely


### Deploy with Kubernetes

The `k8s.yaml` manifest will provision:
- A `safely-listener` Deployment
- A `safely-moderator` Deployment
- A `safely-redis` Deployment
  - An instance of redis used for communication by the various celery components
- A `safely-redis` Service so that the redis instance can be accessed by hostname
- A `safely-config` Configmap
- A `safely-slackbot-token` Secret

Assuming you have the slackbot token already saved in a file, you can deploy with the command below, by specifying the path to your token file.

`sed "s/SLACKBOT_TOKEN_PLACEHOLDER/$(cat PATH/TO/FILE/WITH/TOKEN)/" k8s.yaml | kubectl apply  -f -`


### Deploy with Docker Compose

- Create a new cloud compute instance with at least 4GB RAM and 4 vCPUs.
- Clone this repo. 
- Install Docker and Docker Compose.
- Start the entire stack with 
    
        docker-compose up -d

### Deploy with Docker.

To run with just Docker:

Run a Celery Broker (Redis or RabbitMQ)

    docker run --rm --name redis -d redis

Start the events listener service

    docker run --rm --name listener --link redis:redis --env-file ./.env -d imichael/safely-listener
    
Start the moderator service

    docker run --rm --name moderator --link redis:redis --env-file .env -d imichael/safely-moderator
    

See `docker-compose.yml` for supported env vars to store in the .env file.
