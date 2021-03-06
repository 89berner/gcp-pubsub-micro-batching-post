FROM      debian:stretch
MAINTAINER Juan Berner

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y gnupg

RUN \
    echo "===> add webupd8 repository..."  && \
    echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main" | tee /etc/apt/sources.list.d/webupd8team-java.list  && \
    echo "deb-src http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main" | tee -a /etc/apt/sources.list.d/webupd8team-java.list  && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 4052245BD4284CDD  && \
    apt-get update


RUN echo "===> install Java"  && \
    echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections  && \
    echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections  && \
    DEBIAN_FRONTEND=noninteractive  apt-get install -y --force-yes oracle-java8-installer oracle-java8-set-default

RUN echo "===> clean up..."  && \
    rm -rf /var/cache/oracle-jdk8-installer  && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*


RUN apt-get update && apt-get install -y nano less ca-certificates wget vim htop procps python3-pip
RUN wget https://artifacts.elastic.co/downloads/logstash/logstash-6.3.2.tar.gz -O /tmp/logstash.tar.gz 2> /dev/null

RUN tar zxvf /tmp/logstash.tar.gz -C /opt && mv /opt/logstash-6.3.2 /opt/logstash && rm -rf /tmp/logstash.tar.gz

RUN mkdir /opt/logs

RUN pip3 install --upgrade pip
ADD requirements.txt /indexer/requirements.txt
RUN pip3 install --upgrade -r /indexer/requirements.txt

ADD logstash.conf /opt/conf/logstash.conf

ADD entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ADD indexer.py /indexer/indexer.py

CMD /usr/local/bin/entrypoint.sh
