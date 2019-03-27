import logging
import traceback
import os
import threading
import re
import sys
import json

# PUBSUB
from google.cloud        import pubsub
from google.cloud        import storage
from google.cloud.pubsub import types

# LOGSTASH SOCKET
import socket

LOGSTASH_HOST = os.environ['LOGSTASH_HOST']
LOGSTASH_PORT = int(os.environ['LOGSTASH_PORT'])
PROJECT_NAME = os.environ['PROJECT_NAME']
SUB_NAME     = os.environ['SUBSCRIPTION_NAME']

SUBSCRIPTION_NAME = 'projects/{project_id}/subscriptions/{sub}'.format(project_id=PROJECT_NAME,sub=SUB_NAME)

gcs_client = storage.Client()
subscriber = pubsub.SubscriberClient()

logging.basicConfig(level=logging.INFO, format='%(relativeCreated)6d %(threadName)s %(message)s')

# SETUP SOCKET, WE SHOULD HAVE LOGIC TO KEEP TRYING IF ITS NOT READY YET
sock       = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((LOGSTASH_HOST, LOGSTASH_PORT))
logging.info("Socket connected on host:%s and port:%s" % (LOGSTASH_HOST, LOGSTASH_PORT) )

def get_gcs_file_data(filename):

    #extract bucketname
    m = re.search('gs://(.+?)/(.*)', filename.decode("utf-8") )
    bucket_name = m.groups()[0]
    filename    = m.groups()[1]

    logging.debug("Will process filename: %s" % filename)
    bucket = gcs_client.bucket(bucket_name)

    blob = bucket.get_blob(filename)
    if (blob is not None):
        data = blob.download_as_string().decode("utf-8")
        logging.debug("Filename %s downloaded.." % filename)
    else:
        logging.error("No data found for file %s" % filename)
        return (False, None, None)

    return (True, data, blob.size)

def pubsub_callback(message):
    try:
        logging.debug("Message received: %s" % message )

        # parse message
        filename = message.data

        logging.info("[%s] Filename retrieved" % filename )
        (found, file_data, size) = get_gcs_file_data(filename)
        if (found):
            logging.debug("[%s] Retrieved %d bytes" % (filename, size) )

            lines = file_data.split("\n")
            logging.debug("[%s] Retrieved %d lines" % (filename, len(lines)) )

            # FOR EACH LINE PRINT
            for line in lines:
                logging.info("Sending line to logstash: %s" % line)
                data = { "message": line }
                data_to_send = json.dumps(data) + "\n"
                sock.sendall(data_to_send.encode('utf-8'))
                
        message.ack()
    except:
        logging.error("Error processing callback: %s" % traceback.format_exc())
        message.nack()

def process_pubsub():
    while(True):
        logging.info("Will subscribe to a Pub/Sub topic")

        future = subscriber.subscribe(SUBSCRIPTION_NAME, pubsub_callback)
        future.result()

        logging.info("Worker finished processing pubsub")

if __name__ == '__main__':
    logging.info("Starting process to get logs from GCS through Pub/Sub...")
    process_pubsub()
