<<<<<<< HEAD
FROM kong:2.6.0-centos
=======
FROM kong:2.4.1-centos
USER root
>>>>>>> cc003dff4e3b2c34d5589c42176f7acdda4ae609
ADD . /
# RUN yum install which -y
RUN cp /etc/kong/kong.conf.default /etc/kong/kong.conf && \
	echo "db_update_propagation = 1" >> /etc/kong/kong.conf
