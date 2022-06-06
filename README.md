# FMI-support-for-digital-twins-platform

In this repository you can find the FMI support for the digital twins platform.

This app is designed to run using Kubernetes, so maybe, you need to make some changes to the code if you want to run it locally. In addition, you will need Kafka in order to send the final data to the consumer.

This app works as follows:

The very first step is making a request to the app using POST, the request will contains all the data needed to run the simulation.
After that, the app will create a Kubernetes job with all the data needed.

This job will make a GET request to obtain the .fmu file and then will execute the simulation according to the introduced parameters.

When the simulation is finished, it will send the resulting data throw Kafka using the Kafka previous sent Kafka topic.

There are two types of simulations:
1. One step simulation: It will simulate al timesteps and then will send the results.
2. Step by step: It will send result in everysingle time step, so it is like a "real time" simulation.
