# Deadreckoner
Python script that creates a virtual AIS target that approximates the ship's position when the gps signal is lost.

![Capture](https://github.com/user-attachments/assets/110de8ab-7bf3-4c3c-9ca8-6cd03dfff744)

To test:

* Clone deadreckoner and run dr.exe.
* It will broadcast AIS-messages of a virtual ship somewhere on the northsea to UDP/10110.
* To visualise this, create an UDP network connection in OpenCPN that 'Receives input' from address 'localhost' and dataport '10110'.
* When you see the AIS plot, change STW in the DR console to '10', and you should see the AIS target moving. Change the HDG heading and the plot turns. Change the DR Interval to '1' for more frequent updates.
* To simulate a moving ship, clone [ais_simulation](https://github.com/marcobergman/ais_simulation) and run simulate_ais.exe. Click start. It will broadcast a whole fleet of ships on the north sea, but also your own ship will start to move.
* Add another connection to OpenCPN, that transmits RMC, HDT and VHW messages to TCP/20221, localhost. The VHW messages are not standard in the sentence list and needs to be added (click Add!). 
* Once dr.exe receives RMC messages, it will make the virtual boat follow the own boat. In the AIS simulator, change course and see how it does that. If the virtual boat is hidden under the own boat, increase the DR interval. 
* If you uncheck 'DR follows GPS', the virtual will still follow the own boat, but now based on dead reckoning.

