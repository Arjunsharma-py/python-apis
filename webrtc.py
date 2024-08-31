import json
import logging
from flask import Flask, request
from flask_cors import CORS
from aiortc import RTCPeerConnection, RTCSessionDescription

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pcs = set()

@app.route("/offer", methods=["POST"])
async def offer():
    params = request.json
    offer = RTCSessionDescription(sdp=params["sdp"]["sdp"], type=params["sdp"]["type"])
    pc = RTCPeerConnection()
    pcs.add(pc)

    # Handle the tracks, e.g., saving the video stream to disk
    recorder = MediaRecorder("output.mp4")

    @pc.on("datachannel")
    def on_datachannel(channel):
        logger.info("Data channel received: %s", channel.label)

    @pc.on("icecandidate")
    def on_icecandidate(candidate):
        logger.info("ICE candidate: %s", candidate)

    @pc.on("track")
    async def on_track(track):
        logger.info("Track received: %s", track.kind)
        if track.kind == "video":
            recorder.addTrack(track)
        await recorder.start()

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return json.dumps({"sdp": pc.localDescription})

@app.route("/ice-candidate", methods=["POST"])
async def ice_candidate():
    params = request.json
    candidate = params["candidate"]

    # Add the candidate directly to the peer connection
    pc = list(pcs)[-1]
    await pc.addIceCandidate(candidate["candidate"])

    return "OK", 200

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run(host="0.0.0.0", port=5000))
