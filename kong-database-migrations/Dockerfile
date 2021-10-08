FROM kong:2.6.0-centos
ADD . /
#RUN yum install which -y
RUN cp /etc/kong/kong.conf.default /etc/kong/kong.conf && \
	echo "db_update_propagation = 1" >> /etc/kong/kong.conf
