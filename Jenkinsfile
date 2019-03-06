pipeline {
  agent any

  stages {
    triggers {
      pollSCM('* * * * *')
    }
    stage('Build') {
      steps {
        echo 'Building..'
      }
    }
  }
}
