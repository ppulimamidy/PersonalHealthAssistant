#!/bin/bash
set -e

# Create extension directories if they don't exist
mkdir -p /usr/share/postgresql/14/extension
mkdir -p /usr/lib/postgresql/14/lib

# Function to install extension
install_extension() {
    local ext_name=$1
    local ext_version=$2
    
    if [ ! -f /usr/share/postgresql/14/extension/${ext_name}.control ]; then
        echo "Installing ${ext_name} extension..."
        apt-get update && apt-get install -y postgresql-contrib
        
        # Create control file
        echo "comment = '${ext_name} extension'" > /usr/share/postgresql/14/extension/${ext_name}.control
        echo "default_version = '${ext_version}'" >> /usr/share/postgresql/14/extension/${ext_name}.control
        echo "module_pathname = '\$libdir/${ext_name}'" >> /usr/share/postgresql/14/extension/${ext_name}.control
        echo "relocatable = true" >> /usr/share/postgresql/14/extension/${ext_name}.control
        
        # Copy files if they exist
        if [ -f /usr/lib/postgresql/14/lib/${ext_name}.so ]; then
            cp /usr/lib/postgresql/14/lib/${ext_name}.so /usr/lib/postgresql/14/lib/
        fi
        if [ -f /usr/share/postgresql/14/extension/${ext_name}--${ext_version}.sql ]; then
            cp /usr/share/postgresql/14/extension/${ext_name}--${ext_version}.sql /usr/share/postgresql/14/extension/
        fi
    fi
}

# Install required extensions
install_extension "uuid-ossp" "1.1"
install_extension "pgcrypto" "1.3"

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "Extensions installation completed" 