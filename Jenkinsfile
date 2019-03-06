pipeline {
  agent any
  environment {
    registryCredential = "dockerhub-inriachile"
    dockerImageName = "inriachile/love-manager:${GIT_BRANCH}"
  }
  triggers {
    pollSCM("* * * * *")
  }
  when {
    branch "ci-develop"
  }
  stages {
    stage("Build Docker image") {
      steps {
        script {
          def dockerImage = docker.build dockerImageName
        }
      }
    }
    stage("Push Docker image") {
      steps {
        script {
          docker.withRegistry("", registryCredential) {
            dockerImage.push()
          }
        }
      }
    }
  }
}
