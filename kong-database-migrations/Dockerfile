FROM kong:1.1.2-centos
ADD . /
RUN chmod 777 /*.sh
RUN chmod +x /docker-entrypoint.sh
RUN yum install which -y
#RUN cp /etc/kong/kong.default.conf /etc/kong/kong.conf && \
#	echo """"
