.. sadrive documentation master file, created by
   sphinx-quickstart on Sat Jun 21 17:46:32 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Sadrive Documentation
=====================

SA Drive (Service Account Drive)
--------------------------------

This project unifies the storage of multiple pre-April 15 2025 Google service accounts (each with 15 GiB) into one logical drive, overcoming per-Drive limits and allowing uploads of very large files (> 14.7 GiB) with progress and parallel transfers.

*New service accounts created after April 15 2025 no longer receive 15 GiB each; this tool targets existing accounts only.*

Why is it needed
~~~~~~~~~~~~~~~~

Google Team Drives (Shared Drives) cap out around 100 GiB. By aggregating many service accounts, Sadrive provides a familiar “Drive” interface backed by ~15 GiB chunks.

How It Works
~~~~~~~~~~~~

1. You provision N service accounts (up to 100 per project).
2. Sadrive's CLI detects which account has enough free space.
3. Files are routed and uploaded automatically—no more manual juggling.

Key Benefits
~~~~~~~~~~~~

- **Mount** your aggregated drive locally for read-only access  
- **Parallel** uploads & downloads (via gclone)  
- **Automatic** splitting of files > 14.7 GiB  
- **Progress** bars, ETA, and fuzzy search built in  
- **Statically typed** codebase with full type hints  

Examples
~~~~~~~~

1. ``sadrive``
   
   .. image:: _static/images/image.png
      :alt: sadrive

2. ``sadrive config set-dir <path>``
   
   .. image:: _static/images/image-1.png
      :alt: sadrive config set-dir

3. ``sadrive rename newname file/folderid``
   
   .. image:: _static/images/image-2.png
      :alt: sadrive rename

4. ``sadrive navigate [optional_folderid]``
   
   .. image:: _static/images/image-3.png
      :alt: sadrive navigate

5. ``sadrive share file/folderid``
   
   .. image:: _static/images/image-4.png
      :alt: sadrive share

6. ``sadrive mount`` (read‑only filesystem)
   
   .. image:: _static/images/image-5.png
      :alt: sadrive mount
   
   .. image:: _static/images/image-6.png
      :alt: sadrive mount view

7. ``sadrive delete file/folderid``
   
   .. image:: _static/images/image-7.png
      :alt: sadrive delete

8. ``sadrive newfolder name [optional_destination_id]``
   
   .. image:: _static/images/image-8.png
      :alt: sadrive newfolder

9. ``sadrive upload path/to/upload [destination_folder_id]``  
   *(If no destination ID is given, uploads to the parent in `config.json`.)*
   
   .. image:: _static/images/image-9.png
      :alt: sadrive upload

10. ``sadrive download folder_id path/to/destination [--transfers int]``  
    *(--transfers = max parallel downloads)*
   
    .. image:: _static/images/image-10.png
       :alt: sadrive download


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   interface
   apireference

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
