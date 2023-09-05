#-*- coding=utf-8 -*-

import os
import argparse
import sys
from logger import Logger
LOG = Logger(__file__)

def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--type', help="The type of NYUtil", required=False)
    parser.add_argument('-d', '--directory', help="Directory", required=False)

    return parser.parse_args()

class NYUtil(object):
    def __init__(self, type='', directory=None):
        self.type = type
        self.directory= directory
        self.log_properties()

    def log_properties(self):
        LOG.info(self.__dict__)

    def traverse_directory(self, directory):
        file_paths = []
        for parent, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(parent, file)
                if file_path not in file_paths:
                    file_paths.append(file_path)
        return file_paths

    def rewrite_markdown(self, file_paths):
        destination_path = os.path.join(self.directory, 'total.md')
        markdown_contents = ""
        for file_path in file_paths:
            if file_path.endswith('md'):
                LOG.info(file_path)
                with open (file_path, 'r') as md_file:
                    content_utf8 = md_file.read()
                    content_uni = content_utf8.decode('utf8')
                    LOG.info(content_uni)
                    markdown_contents = "{}{}".format(markdown_contents, content_uni)
        with open(destination_path, 'w') as dest_file:
            dest_file.writelines(markdown_contents)

    def print_dir(self):
        LOG.info("sys.path[0] = ", sys.path[0])
        LOG.info("sys.argv[0] = ", sys.argv[0])
        LOG.info("__file__ = ", __file__)
        LOG.info("os.path.abspath(__file__) = ", os.path.abspath(__file__))
        LOG.info("os.path.realpath(__file__) = ", os.path.realpath(__file__))
        LOG.info("os.path.dirname(os.path.realpath(__file__)) = ",
            os.path.dirname(os.path.realpath(__file__)))
        LOG.info("os.path.split(os.path.realpath(__file__)) = ",
            os.path.split(os.path.realpath(__file__)))
        LOG.info("os.path.split(os.path.realpath(__file__))[0] = ",
            os.path.split(os.path.realpath(__file__))[0])
        LOG.info("os.getcwd() = ", os.getcwd())
if __name__ == "__main__":
    args = read_args()
    LOG.info(args)
    util = NYUtil(type=args.type, directory=args.directory)
    file_paths = util.traverse_directory(directory=args.directory)
    util.rewrite_markdown(file_paths=file_paths)
