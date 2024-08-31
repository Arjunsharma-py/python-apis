# from flask import Flask
# from flask_socketio import SocketIO
# from flask_cors import CORS
# import os
# import ffmpeg
# import logging

# app = Flask(__name__)
# CORS(app)
# socketio = SocketIO(app, cors_allowed_origins="*")

# video_file = "received_video.webm"
# video_chunks = []

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# @socketio.on("video_chunk")
# def handle_video_chunk(data):
#     try:
#         video_chunks.append(data)
#         logger.info("video chunk received!")
#     except Exception as e:
#         logger.error(f"Error handling video chunk: {e}")

# @socketio.on("stop_recording")
# def handle_stop_recording():
#     global video_chunks

#     try:
#         if not video_chunks:
#             logger.warning("No video chunks received.")
#             return

#         # Save the video chunks to a WebM file
#         with open(video_file, "wb") as f:
#             for chunk in video_chunks:
#                 f.write(chunk)

#         logger.info(f"WebM file saved as {video_file}")

#         # Convert the WebM file to MP4 using ffmpeg
#         output_file = "final_video.mp4"
#         try:
#             ffmpeg.input(video_file).output(output_file).run(overwrite_output=True)
#             logger.info(f"Video converted and saved as {output_file}")
#         except ffmpeg.Error as e:
#             logger.error(f"Error converting WebM to MP4: {e}")
        
#         # Clean up
#         video_chunks.clear()
#         if os.path.exists(video_file):
#             os.remove(video_file)
#             logger.info(f"Temporary WebM file {video_file} removed.")
#     except Exception as e:
#         logger.error(f"Error during video processing: {e}")

# if __name__ == "__main__":
#     socketio.run(app, host="0.0.0.0", port=5000)

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import os
import ffmpeg
import logging

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

chunk_counter = 0
chunk_files = []

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@socketio.on("video_chunk")
def handle_video_chunk(data):
    global chunk_counter, chunk_files

    try:
        # Save the chunk as a temporary WebM file
        chunk_filename = f"chunk_{chunk_counter}.webm"
        with open(chunk_filename, "wb") as f:
            f.write(data)
        
        logger.info(f"Saved {chunk_filename}")

        # Verify the file was created successfully
        if not os.path.exists(chunk_filename):
            logger.error(f"File {chunk_filename} was not created.")
            return

        # Convert the WebM chunk to MP4
        mp4_chunk_filename = f"chunk_{chunk_counter}.mp4"
        try:
            (
                ffmpeg
                .input(chunk_filename)
                .output(mp4_chunk_filename, vcodec='libx264', acodec='aac')
                .run(overwrite_output=True)
            )
            logger.info(f"Converted {chunk_filename} to {mp4_chunk_filename}")
            chunk_files.append(mp4_chunk_filename)
        except ffmpeg.Error as e:
            logger.error(f"Error converting {chunk_filename} to MP4: {e}")

        # Clean up the WebM chunk file
        os.remove(chunk_filename)

        chunk_counter += 1

    except Exception as e:
        logger.error(f"Error handling video chunk: {e}")

@socketio.on("stop_recording")
def handle_disconnect():
    global chunk_files, chunk_counter

    if not chunk_files:
        logger.warning("No MP4 chunks to combine.")
        return

    try:
        # Create a file list for ffmpeg to concatenate the chunks
        with open("file_list.txt", "w") as file_list:
            for mp4_chunk in chunk_files:
                file_list.write(f"file '{mp4_chunk}'\n")

        # Concatenate all MP4 chunks into a single MP4 file
        final_output_file = "final_video.mp4"
        try:
            (
                ffmpeg
                .input("file_list.txt", format="concat", safe=0)
                .output(final_output_file, c="copy")
                .run(overwrite_output=True)
            )
            logger.info(f"Final video saved as {final_output_file}")
        except ffmpeg.Error as e:
            logger.error(f"Error concatenating MP4 chunks: {e}")

        # Clean up
        for mp4_chunk in chunk_files:
            os.remove(mp4_chunk)
        os.remove("file_list.txt")

        # Reset counters and file lists
        chunk_files.clear()
        chunk_counter = 0

    except Exception as e:
        logger.error(f"Error during final video processing: {e}")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
