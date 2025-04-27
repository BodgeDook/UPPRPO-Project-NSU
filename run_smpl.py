import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run SMPL model with OpenPose keypoints")
    parser.add_argument("-frames_dir", type=str, required=True, help="Directory containing frames")
    parser.add_argument("-keypoints_dir", type=str, required=True, help="Directory containing keypoints")
    parser.add_argument("-output_dir", type=str, required=True, help="Directory to save output")
    parser.add_argument("-openpose_dir", type=str, default="openpose", help="Directory containing OpenPose executable")
    args = parser.parse_args()

    FRAMES_DIR = args.frames_dir
    KEYPOINTS_DIR = args.keypoints_dir
    OUTPUT_DIR = args.output_dir
    OPENPOSE_DIR = args.openpose_dir

    # Getting openpose keypoints
    subprocess.run("cd $OPENPOSE_DIR && ./build/examples/openpose/openpose.bin --image_dir $FRAMES_DIR --write_json $KEYPOINTS_DIR --display 0 --write_images $OPENPOSE_IMAGES_DIR", shell=True, check=True)

    # Running SMPL model
    subprocess.run("/opt/conda/envs/smpl_venv_2/bin/python smplifyx/main.py --config cfg_files/fit_smplx.yaml \
    --data_folder  ../data \
    --output_folder ../data/smplifyx_results \
    --visualize=True \
    --gender=$gender \
    --model_folder ../smplx/models \
    --vposer_ckpt ../vposer/V02_05\
    --part_segm_fn smplx_parts_segm.pkl")
if __name__ == "__main__":
    main()