-- Set root password for both localhost and 127.0.0.1
ALTER USER 'root'@'localhost'
IDENTIFIED VIA mysql_native_password
USING PASSWORD('root');

ALTER USER 'root'@'127.0.0.1'
IDENTIFIED VIA mysql_native_password
USING PASSWORD('root');

-- Reload privileges so changes take effect immediately
FLUSH PRIVILEGES;

-- Enable SSL for some reason
FLUSH SSL;

SHUTDOWN;
