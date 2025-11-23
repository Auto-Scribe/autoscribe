import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from autoscribe import load_midi
from autoscribe.core.musicxml_exporter import MusicXMLExporter, export_to_musicxml
from typing import Optional
import os


def convert_midi_to_sheet_music(
    midi_path: str,
    output_path: Optional[str] = None,
    title: Optional[str] = None,
    auto_quantize: bool = True,
    open_in_musescore: bool = False,
):
    """
    Complete MIDI to sheet music conversion.
    """
    from typing import Optional

    print(f"\n{'='*70}")
    print("AutoScribe: MIDI to Sheet Music Conversion")
    print(f"{'='*70}")
    print(f"Input: {Path(midi_path).name}")

    # Determine output path
    if output_path is None:
        base_name = Path(midi_path).stem
        output_path = f"{base_name}_sheet_music.musicxml"

    # Determine title
    if title is None:
        title = Path(midi_path).stem.replace("_", " ").title()

    print(f"Output: {output_path}")
    print(f"Title: {title}")
    print(f"Auto-quantize: {auto_quantize}")

    # Load MIDI
    print("\n" + "=" * 70)
    piano_roll = load_midi(midi_path)

    # Export to MusicXML
    exporter = MusicXMLExporter(
        auto_quantize=auto_quantize,
        auto_detect_chords=True,
        auto_separate_voices=True,
        auto_assign_hands=True,
    )

    output_file = exporter.export(piano_roll, output_path, title)

    # Summary
    print(f"\n{'='*70}")
    print("Conversion Summary")
    print(f"{'='*70}")
    print(f"✓ Input MIDI: {midi_path}")
    print(f"✓ Output MusicXML: {output_file}")
    print(f"✓ File size: {os.path.getsize(output_file):,} bytes")

    print(f"\n{'='*70}")
    print("Next Steps:")
    print(f"{'='*70}")
    print(f"1. Open the file in MuseScore, Finale, or Sibelius:")
    print(f"   File → Open → {output_file}")
    print(f"\n2. Edit the sheet music as needed")
    print(f"\n3. Export to PDF:")
    print(f"   File → Export → PDF")

    # open in MuseScore
    if open_in_musescore:
        print(f"\nAttempting to open in MuseScore...")
        try:
            import subprocess

            musescore_commands = [
                "musescore",
                "musescore3",
                "musescore4",
                "/Applications/MuseScore 3.app/Contents/MacOS/mscore",
                "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
                "C:\\Program Files\\MuseScore 3\\bin\\MuseScore3.exe",
                "C:\\Program Files\\MuseScore 4\\bin\\MuseScore4.exe", 
            ]

            opened = False
            for cmd in musescore_commands:
                try:
                    subprocess.Popen([cmd, output_file])
                    print(f"✓ Opened in MuseScore")
                    opened = True
                    break
                except (FileNotFoundError, OSError):
                    continue

            if not opened:
                print("⚠ MuseScore not found. Please open the file manually.")

        except Exception as e:
            print(f"⚠ Could not auto-open: {e}")

    return output_file


def batch_convert(midi_directory: str, output_directory: str = "sheet_music"):
    """
    Convert all MIDI files in a directory to sheet music.

    Args:
        midi_directory: Directory containing MIDI files
        output_directory: Directory for output files
    """
    print(f"\n{'='*70}")
    print("Batch Conversion")
    print(f"{'='*70}")

    # Create output directory
    os.makedirs(output_directory, exist_ok=True)

    # Find all MIDI files
    midi_files = []
    for ext in ["*.mid", "*.midi"]:
        midi_files.extend(Path(midi_directory).glob(ext))

    if not midi_files:
        print(f"No MIDI files found in {midi_directory}")
        return

    print(f"Found {len(midi_files)} MIDI files")

    # Convert each file
    successful = 0
    failed = 0

    for i, midi_file in enumerate(midi_files, 1):
        print(f"\n[{i}/{len(midi_files)}] Converting {midi_file.name}...")

        try:
            output_path = Path(output_directory) / f"{midi_file.stem}.musicxml"
            convert_midi_to_sheet_music(
                str(midi_file),
                str(output_path),
                auto_quantize=True,
                open_in_musescore=False,
            )
            successful += 1
        except Exception as e:
            print(f"✗ Failed: {e}")
            failed += 1

    # Summary
    print(f"\n{'='*70}")
    print("Batch Conversion Summary")
    print(f"{'='*70}")
    print(f"Total files: {len(midi_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {output_directory}")


def main():
    """Main test function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert MIDI files to sheet music (MusicXML)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file
  python test_musicxml_exporter.py song.mid
  
  # Convert with custom output path
  python test_musicxml_exporter.py song.mid -o my_sheet_music.musicxml
  
  # Convert with custom title
  python test_musicxml_exporter.py song.mid --title "My Song"
  
  # Disable auto-quantization
  python test_musicxml_exporter.py song.mid --no-quantize
  
  # Try to open in MuseScore
  python test_musicxml_exporter.py song.mid --open
  
  # Batch convert directory
  python test_musicxml_exporter.py --batch midi_files/
        """,
    )

    parser.add_argument("midi_file", nargs="?", help="Path to MIDI file")
    parser.add_argument("-o", "--output", help="Output MusicXML path")
    parser.add_argument("--title", help="Title for the piece")
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="Disable automatic rhythm quantization",
    )
    parser.add_argument(
        "--open", action="store_true", help="Try to open result in MuseScore"
    )
    parser.add_argument(
        "--batch", metavar="DIR", help="Batch convert all MIDI files in directory"
    )

    args = parser.parse_args()

    try:
        if args.batch:
            # Batch mode
            batch_convert(args.batch)
        elif args.midi_file:
            # Single file mode
            if not Path(args.midi_file).exists():
                print(f"File not found: {args.midi_file}")
                return 1

            convert_midi_to_sheet_music(
                args.midi_file,
                args.output,
                args.title,
                auto_quantize=not args.no_quantize,
                open_in_musescore=args.open,
            )
        else:
            parser.print_help()
            return 1

        print("\n Conversion completed successfully!")
        return 0

    except Exception as e:
        print(f"\n Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
