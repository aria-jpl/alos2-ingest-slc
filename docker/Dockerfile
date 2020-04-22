FROM hysds/isce2:latest

MAINTAINER aria-ops "aria-ops@list.jpl.nasa.gov"
LABEL description="GRFN PGE container"



USER ops


# copy ariamh code ensure proper permissions, and move dependencies to final locations
COPY . /home/ops/verdi/ops/alos2-ingest-slc
RUN set -ex \
 && sudo rm -rf /root/.cache \
 && sudo chown -R ops:ops /home/ops/verdi/ops/alos2-ingest-slc 

# set entrypoint
WORKDIR /home/ops
CMD ["/bin/bash", "--login"]
