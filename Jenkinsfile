pipeline {
  agent{
    docker {
      alwaysPull true
      image 'lsstts/develop-env:develop'
      args "--entrypoint=''"
    }
  }
  environment {
    dockerImage = ""
    // LTD credentials
    user_ci = credentials('lsst-io')
    LTD_USERNAME="${user_ci_USR}"
    LTD_PASSWORD="${user_ci_PSW}"
  }

  stages {
    stage("Run pre-commit hooks and tests") {
      steps {
        script {
          sh """
            source /home/saluser/.setup_dev.sh

            generate_pre_commit_conf --skip-pre-commit-install
            pre-commit run --all-files

            cd ./manager

            pip install -r requirements.txt
            pytest
          """
        }
      }
    }

    stage("Deploy documentation") {
      when {
        anyOf {
          branch "main"
          branch "develop"
        }
      }
      steps {
        script {
          sh """
            source /home/saluser/.setup_dev.sh

            # Create docs
            cd ./docsrc
            pip install -r requirements.txt
            sh ./create_docs.sh
            cd ..

            # Upload docs
            pip install ltd-conveyor
            ltd upload --product love-manager --git-ref ${GIT_BRANCH} --dir ./docs
          """
        }
      }
    }
  }
}
