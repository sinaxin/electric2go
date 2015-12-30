# coding=utf-8

from __future__ import print_function
import os
import stat
import json

from . import cmdline, generate
from .. import cars, systems
from . import stats as process_stats, graph as process_graph


def make_graph_from_frame(result_dict, data, animation_files_prefix, symbol,
                          show_speeds, distance, tz_offset):
    index, turn, current_positions, current_trips = data

    image_filename = '{file}_{i:05d}.png'.format(file=animation_files_prefix, i=index)

    process_graph.make_graph(result_dict, current_positions, current_trips,
                             image_filename, turn,
                             show_speeds, distance, symbol, tz_offset)

    return image_filename


def process_web(iter_filenames):
    # TODO: consider removing this functionality, it's, like, never been used
    # and the mode is highly inefficient - so much easier to load a proper video
    # than to make a hobo-video from individual images in JS,
    # and the individual image (where it might be more accessible than JS canvas)
    # is not really served by this function anyway.

    filenames_file_name = cars.output_file_name('filenames', 'json')
    with open(filenames_file_name, 'w') as f:
        json.dump(iter_filenames, f)

    crushed_dir = cars.output_file_name('crushed-images')
    if not os.path.exists(crushed_dir):
        os.makedirs(crushed_dir)

    crush_commands = ['pngcrush %s %s' %
                      (filename, os.path.join(crushed_dir, os.path.basename(filename)))
                      for filename in iter_filenames]

    command_file_name = cars.output_file_name('pngcrush')
    with open(command_file_name, 'w') as f:
        f.write('\n'.join(crush_commands))
    os.chmod(command_file_name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    return command_file_name


def make_animate_command(result_dict, animation_files_prefix, frame_count):
    background_path = systems.get_background_as_image(result_dict)
    png_filepaths = animation_files_prefix + '_%05d.png'
    mp4_path = animation_files_prefix + '.mp4'

    framerate = 30
    # to my best understanding, my "input" is the static background image
    # which avconv assumes to be "25 fps".
    # to get output at 30 fps to be correct length to include all frames,
    # I need to convert framecount from 25 fps to 30 fps
    frames = (frame_count / 25.0) * framerate

    command_template = "avconv -loop 1 -r %d -i %s -vf 'movie=%s [over], [in][over] overlay' -b 15360000 -frames %d %s"
    command = command_template % (framerate, background_path, png_filepaths, frames, mp4_path)

    return command


def make_video_frames(result_dict, distance, show_move_lines, show_speeds, symbol, tz_offset):
    # set up params for iteratively-named images
    city = result_dict['metadata']['city']
    animation_files_prefix = cars.output_file_name(description=city)

    # make_graph_from_frame is currently fairly slow (~2 seconds per frame).
    # The map can be fairly easily parallelized, e.g. http://stackoverflow.com/a/5237665/1265923
    # TODO: parallelize
    # It appears process_graph functions will be safe to parallelize, they
    # all ultimately go to matplotlib which is parallel-safe
    # according to http://stackoverflow.com/a/4662511/1265923
    generated_images = [
        make_graph_from_frame(result_dict, data, animation_files_prefix, symbol,
                              show_speeds, distance, tz_offset)
        for data in generate.build_data_frames(result_dict, show_move_lines)
    ]

    animate_command_text = make_animate_command(result_dict, animation_files_prefix, len(generated_images))

    return animate_command_text, generated_images


def batch_process(video=False, web=False, tz_offset=0, stats=False,
                  show_move_lines=True, show_speeds=False, symbol='.', distance=False,
                  all_positions_image=False, all_trips_lines_image=False, all_trips_points_image=False):
    """
    :return: does not return anything
    """

    # read in all data
    result_dict = cmdline.read_json()

    # generate images
    if video:
        animate_command_text, generated_images = make_video_frames(result_dict, distance,
                                                                   show_move_lines, show_speeds,
                                                                   symbol, tz_offset)

        # print animation information if applicable
        if web:
            crush_command_file = process_web(generated_images)
            print('\nto pngcrush:')
            print('./' + crush_command_file)

        # print animation information
        print('\nto animate:')
        print(animate_command_text)

    if stats:
        written_file = process_stats.stats(result_dict, tz_offset)
        print(written_file)  # provide output name for easier reuse

    if all_positions_image:
        process_graph.make_positions_graph(result_dict, all_positions_image, symbol)

    if all_trips_lines_image:
        process_graph.make_trips_graph(result_dict, all_trips_lines_image)

    if all_trips_points_image:
        process_graph.make_trip_origin_destination_graph(result_dict, all_trips_points_image, symbol)
