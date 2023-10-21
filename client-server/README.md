# BOOT: Client SBC Server

This self-contradictorily named subpackage provided a web server (at port 5000) with three functions:

- Remote starting of the play from Blender

- Easy hot reloading (of the server *and all other client code*)

- A web interface to interact with hardware functionality, generated from introspection

It should be launched with the scripts provided in `client-scripts`

## Warning

This server has a huge attack surface and no built-in security. Do not run it outside a trusted environment.
