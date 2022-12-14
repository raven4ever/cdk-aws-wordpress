#!/bin/bash

yum update -y
yum -y install amazon-efs-utils nfs-utils

mkdir -p /var/www/html
echo "%$%efs_id.efs.%$%region.amazonaws.com:/ /var/www/html nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport,_netdev 0 0" >> /etc/fstab
mount -t efs %$%efs_id /var/www/html

yum -y install nginx php70-fpm php70-intl php70-common php70-mysqli php70-curl jq
chkconfig nginx on

#start wp conf vhost
cat > /etc/nginx/conf.d/wp.conf <<EOL
server {
    listen 80;
    server_name *.eu-central-1.elb.amazonaws.com;

    root /var/www/html;
    index index.php;
    charset UTF-8;

    ##
    # gzip config
    ##

    gzip on;
    gzip_static on;
    gzip_vary on;
    gzip_disable "msie6";
    gzip_types text/css text/x-component application/x-javascript application/javascript text/javascript text/x-js text/richtext image/svg+xml text/plain text/xsd text/xsl
text/xml image/x-icon;
    gzip_http_version 1.1;
    gzip_comp_level 6;
    gzip_proxied any;

    ##
    # Server log config
    ##

    access_log off;
    error_log /var/log/nginx/error.log warn;

    ##
    # FastCGI cache exceptions
    ##

    set \$no_cache 0;
    set \$cache_uri \$request_uri;
    if (\$request_method = POST) {
        set \$cache_uri "null cache";
        set \$no_cache 1;
    }
    if (\$query_string != "") {
        set \$cache_uri "null cache";
        set \$no_cache 1;
    }
    if (\$request_uri ~* "(/wp-admin/|/xmlrpc.php|/wp-(app|cron|login|register|mail).php|wp-.*.php|/feed/|index.php|wp-comments-popup.php|wp-links-opml.php|wp-locations.php|sitemap(_index)?.xml|[a-z0-9_-]+-sitemap([0-9]+)?.xml)") {
        set \$cache_uri "null cache";
        set \$no_cache 1;
    }
    if (\$http_cookie ~* "comment_author|wordpress_[a-f0-9]+|wp-postpass|wordpress_logged_in") {
        set \$cache_uri "null cache";
        set \$no_cache 1;
    }

    ##
    # Browser cache config
    location ~ \.(css|htc|js|js2|js3|js4)$ {
        expires max;
        add_header Pragma "public";
        add_header Cache-Control "max-age=31536000, public, must-revalidate, proxy-revalidate";
    }

    location ~ \.(html|htm|rtf|rtx|svg|svgz|txt|xsd|xsl|xml)$ {
        expires 3600s;
        add_header Pragma "public";
        add_header Cache-Control "max-age=3600, public, must-revalidate, proxy-revalidate";
    }

    location ~ \.(asf|asx|wax|wmv|wmx|avi|bmp|class|divx|doc|docx|eot|exe|gif|gz|gzip|ico|jpg|jpeg|jpe|json|mdb|mid|midi|mov|qt|mp3|m4a|mp4|m4v|mpeg|mpg|mpe|mpp|otf|odb|odc|odf|odg|odp|ods|odt|ogg|pdf|png|pot|pps|ppt|pptx|ra|ram|svg|svgz|swf|tar|tif|tiff|ttf|ttc|wav|wma|wri|xla|xls|xlsx|xlt|xlw|zip)$ {
        expires max;
        add_header Pragma "public";
        add_header Cache-Control "max-age=31536000, public, must-revalidate, proxy-revalidate";
        log_not_found off;
    }

    ##
    # Favicon
    ##

    location = /favicon.ico {
        log_not_found off;
        access_log off;
    }

    ##
    # robots.txt
    ##

    location = /robots.txt {
        allow all;
        log_not_found off;
        access_log off;
    }

    ##
    ##
    # Deny access to hidden files
    ##

    location ~ /\. {
        deny all;
    }

    ##
    # Deny access to uploaded PHP files
    ##

    location ~* /(?:uploads|files)/.*\.php$ {
        deny all;
    }

    ##
    # Deny access to WordPress include-only files
    ##

    location ~ ^/wp-admin/includes/ {
        deny all;
        }
    location ~ ^/wp-includes/[^/]+\.php$ {
        deny all;
    }
    location ~ ^/wp-includes/js/tinymce/langs/.+\.php {
        deny all;
    }
    location ~ ^/wp-includes/theme-compat/ {
        deny all;
    }

    location / {
        try_files \$uri \$uri/ /index.php?q=\$uri&\$args;
    }
    location ~ \.php$ {
        try_files \$uri =404;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
        fastcgi_split_path_info ^(.+\.php)(/.+)$;
        fastcgi_index index.php;
         fastcgi_intercept_errors on; fastcgi_keep_conn on; fastcgi_read_timeout 300; fastcgi_pass 127.0.0.1:9000;
         #fastcgi_pass unix:/var/run/php5-fpm.sock;
        ##
        # FastCGI cache config
        ##
        # fastcgi_cache_path /var/cache/nginx levels=1:2 keys_zone=WORDPRESS:10m max_size=1000m inactive=60m; fastcgi_cache_key \$scheme\$host\$request_uri\$request_method;
        # fastcgi_cache_use_stale updating error timeout invalid_header http_500;
        fastcgi_no_cache \$no_cache;
        fastcgi_cache_bypass \$no_cache;
        #fastcgi_cache WORDPRESS;
        fastcgi_cache_valid any 30m;
    }
}
EOL
#END wp conf vhost

service php-fpm start
service nginx start

rm /var/www/html/index.html

wget https://wordpress.org/latest.zip
unzip latest.zip

mv wordpress/* /var/www/html

chown www-data: /var/www/html -R

mv /var/www/html/wp-config-sample.php /var/www/html/wp-config.php

db_name=`aws secretsmanager get-secret-value --region %$%region --secret-id %$%rds_secret_id --query SecretString --output text | jq -r .dbname`
db_user=`aws secretsmanager get-secret-value --region %$%region --secret-id %$%rds_secret_id --query SecretString --output text | jq -r .username`
db_password=`aws secretsmanager get-secret-value --region %$%region --secret-id %$%rds_secret_id --query SecretString --output text | jq -r .password`
db_url=`aws secretsmanager get-secret-value --region %$%region --secret-id %$%rds_secret_id --query SecretString --output text | jq -r .host`

sed -i "s/database_name_here/$db_name/g" /var/www/html/wp-config.php
sed -i "s/username_here/$db_user/g" /var/www/html/wp-config.php
sed -i "s/password_here/$db_password/g" /var/www/html/wp-config.php
sed -i "s/localhost/$db_url/g" /var/www/html/wp-config.php

echo session.save_handler = redis >> /etc/php.ini
echo session.save_path = \"tcp://%$%redis_url:6379\" >> /etc/php.ini

service php-fpm restart
