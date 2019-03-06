pipeline {
  agent any

  stages {
    stage('Build') {
      triggers {
        pollSCM('* * * * *')
      }
      steps {
        echo 'Building..'
      }
    }
  }
}
