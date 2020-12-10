from graphical_interface import GraphicalInterface
import logging

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s: %(message)s', level=logging.INFO)
    app = GraphicalInterface(image_size=(640, 480),
                            robot_init_pos=[100, 75, 50, 0],
                            logging_level = 'INFO')
    app.run()