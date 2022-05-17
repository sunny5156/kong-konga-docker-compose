FROM kong:2.7.1-centos
ADD . /
RUN cp /etc/kong/kong.conf.default /etc/kong/kong.conf && \
	echo "db_update_propagation = 1" >> /etc/kong/kong.conf
