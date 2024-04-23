FROM kong/kong-gateway:3.5-rhel
ADD . /
#RUN yum install which -y
RUN cp /etc/kong/kong.conf.default /etc/kong/kong.conf && \
	echo "db_update_propagation = 1" >> /etc/kong/kong.conf
