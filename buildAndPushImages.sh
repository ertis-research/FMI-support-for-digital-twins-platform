sudo docker build --network=host -t localhost:5000/restapifmi RestAPI/.
sudo docker push localhost:5000/restapifmi

sudo docker build --network=host -t localhost:5000/fmurunner FMUrunner/.
sudo docker push localhost:5000/fmurunner