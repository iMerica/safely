# Safely    


<a href="https://slack.com/oauth/authorize?scope=incoming-webhook,bot&client_id=115805408818.512365107591">
    <img alt="Add to Slack" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" 
    srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" />
</a>

(Pending Approval From Slack)

# Background

This is a Slack bot that uses machine learning to infer if anything posted to Slack is NSFW. 


# Architecture

There are two core services involved

- Safely Listener, The Real Time Slack events processor that dispatches classification tasks. 
- Safely Moderator, The Classifier that receives tasks from the real time listener and makes inferences about content.


# Usage

If you don't want to bother deploying this and running your own infrastructure, you can join 
[Safely](http://safely.chat/) (coming soon), which is a paid content moderation service that provides the 
same capability in addition to:
 
 - Fine tuning inference parameters.
 - Continuously trained classification models.
 - Custom reporting and behaviors.
 - Additional content-moderation insights.
 - Daily/Weekly digests. 


### Initial Setup.
If you prefer to run this yourself, follow these initial steps

- Create a Slack App and Bot app in Slack.
- export your Slack token as `SAFELY_SLACKBOT_TOKEN=<your token>`.
- export your list of Slack admins as `SAFELY_ADMINS_LIST=@michael,@admin` (separated by a comma). 
- Invite your Slack bot to all the channels you would like to monitor.


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
    
    
## Disclaimer

- Safely focuses on basic NSFW content including nudity and profanity. See the Open NSFW
  project for further information about the scope of the model. 
  
- This tool is imperfect. There will be some false positives & negatives. Please see the license file to learn more
  about guarantees (there are none).


# Credits

Special thanks to:
 
 - [Yahoo's NSFW Model](https://github.com/yahoo/open_nsfw/), which has been converted from Caffe to 
Tensorflow.

-  [Profanity Check](https://github.com/vzhou842/profanity-check), which provides a model trained by Sci Kit learn 
(not a black list) 



# License
MIT