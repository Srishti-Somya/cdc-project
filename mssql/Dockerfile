FROM mcr.microsoft.com/mssql/server:2022-latest

USER root

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and Microsoft packages cleanlyRUN apt-get update && \
    RUN apt-get update && \
    apt-get install -y curl gnupg apt-transport-https && \
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg && \
    curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools unixodbc-dev && \
    echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc && \
    ln -s /opt/mssql-tools/bin/sqlcmd /usr/bin/sqlcmd && \
    ln -s /opt/mssql-tools/bin/bcp /usr/bin/bcp && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


ENV PATH="${PATH}:/opt/mssql-tools/bin"

# Copy init and entrypoint scripts
COPY init.sql /init.sql
COPY entrypoint.sh /entrypoint.sh

COPY mssql.conf /etc/mssql/mssql.conf

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

ENV ACCEPT_EULA=Y
ENV SA_PASSWORD=Srishti!sqlw0rd

CMD ["/entrypoint.sh"]
