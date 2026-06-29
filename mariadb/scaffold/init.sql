-- Set root password for both localhost and 127.0.0.1
ALTER USER 'root'@'localhost'
IDENTIFIED BY 'root';

ALTER USER 'root'@'127.0.0.1'
IDENTIFIED BY 'root';

-- Reload privileges so changes take effect immediately
FLUSH PRIVILEGES;

-- Enable SSL for some reason
FLUSH SSL;

SHUTDOWN;
