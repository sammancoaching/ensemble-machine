login()
{
   ssh -i ~/.ssh/projector.pem ubuntu@$1
}

login $1

