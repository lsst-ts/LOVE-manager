ARG cycle=develop
ARG py_version=3.13

FROM ts-dockerhub.lsst.org/conda_package_builder:latest AS builder

ARG py_version

WORKDIR /tmp/build
COPY . .

RUN source /home/saluser/.setup.sh && \
    CONDA_BLD_PATH=/tmp/conda-bld conda build --python ${py_version} -c lsstts/label/main --prefix-length 100 --no-test conda/

FROM ts-dockerhub.lsst.org/deploy-env:${cycle}

LABEL maintainer Sebastian Aranda <sebastian.aranda@noirlab.edu>

WORKDIR /home/saluser/develop

COPY --chown=saluser:saluser --from=builder /tmp/conda-bld /tmp/conda-bld
COPY --chown=saluser:saluser . .

RUN source /home/saluser/.setup_sal_env.sh && \
	conda index /tmp/conda-bld && \
    conda install -c file:///tmp/conda-bld love-manager -y && \
    conda clean -afy && \
    rm -rf /tmp/conda-bld

# Copy source code and build project
RUN source /home/saluser/.setup_sal_env.sh && \
    python python/love/manager/manage.py collectstatic --noinput

# Expose static files and port
#VOLUME /usr/src/love/manager/static
#VOLUME /usr/src/love/manager/media
EXPOSE 8000

# Set env variables for runtime (to be replaced in docker-compose files)
ENV ADMIN_USER_PASS=test
ENV USER_USER_PASS=test
ENV CMD_USER_PASS=test
ENV NO_DEBUG=True

ENV DB_ENGINE=postgresql
ENV DB_NAME=postgres
ENV DB_USER=postgres
ENV DB_PASS=postgres
ENV DB_HOST=database
ENV DB_PORT=5432

# Run uvicorn server in runtime
COPY --chown=saluser:saluser docker/runserver.sh /home/saluser/.startup.sh
RUN chmod a+x /home/saluser/.startup.sh
