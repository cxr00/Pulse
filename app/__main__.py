from app import Pulse
from triage import Prompt


def main():
    app = Pulse(prompts=Prompt.load_folder("local"))
    app.run()


if __name__ == '__main__':
    main()
