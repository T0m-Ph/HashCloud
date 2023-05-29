FROM ubuntu:latest

ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update -y
RUN apt -y install unzip awscli hashcat

RUN useradd -m hashcat
USER hashcat
COPY run.sh /tmp/run.sh
