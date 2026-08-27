UV ?= uv
PYTHON := $(UV) run --python 3.11

.PHONY: bootstrap validate music sfx compile compile-minimal portability smoke play capture journey mechanics title-flow tam-survival input-playthrough suspend-continue gui-navigation game-over-recovery package package-smoke editor editor-smoke report test lint determinism check clean

bootstrap:
	git submodule update --init --recursive
	$(UV) sync --python 3.11 --extra dev
	$(UV) pip install --python .venv/bin/python -r vendor/lt-maker/requirements_editor.txt

validate:
	$(PYTHON) winternight validate

music:
	$(PYTHON) python -m winternight_gen.music_pipeline design/music.yaml assets/music

sfx:
	$(PYTHON) python -m winternight_gen.sfx_pipeline design/sfx.yaml assets/sfx

compile:
	$(PYTHON) winternight compile

compile-minimal:
	$(PYTHON) winternight compile-minimal

portability:
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) pytest tests/test_portability.py

smoke:
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight smoke

play: compile
	$(PYTHON) winternight play

capture: compile
	$(PYTHON) winternight capture

journey: compile
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight journey

mechanics: compile
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight mechanics

title-flow: compile
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight title-flow

tam-survival: compile
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight tam-survival

input-playthrough: compile
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight input-playthrough

suspend-continue: compile
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight suspend-continue

gui-navigation: compile
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight gui-navigation

game-over-recovery: compile
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight game-over-recovery

package: compile
	$(PYTHON) winternight package

package-smoke: package
	SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight package-smoke

editor: compile
	$(PYTHON) winternight editor

editor-smoke:
	QT_QPA_PLATFORM=offscreen SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $(PYTHON) winternight editor-smoke

report:
	$(PYTHON) winternight report

test:
	$(PYTHON) pytest

lint:
	$(PYTHON) ruff check src tests

determinism:
	$(PYTHON) winternight determinism

check: validate compile lint test smoke title-flow mechanics tam-survival journey editor-smoke determinism input-playthrough suspend-continue gui-navigation game-over-recovery capture package-smoke report

clean:
	$(PYTHON) winternight clean
