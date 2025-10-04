// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
use dirs::home_dir;
use sahomedb::prelude::*;

// Vector dimension must be uniform.
const DIMENSION: usize = 128;

// Connect to Vector Database
pub fn connect_db() -> Option<Database> {
    let db_path = &get_db_path();

    let vector_db = Some(Database::open(db_path).expect("Failed to open database"));
    vector_db
}

// Add to collection
pub fn add_to_collection() {
    let vector_db = connect_db();
    let records = Record::many_random(DIMENSION, 100);
    let mut config = Config::default();

    config.distance = Distance::Cosine;

    let collection = Collection::build(&config, &records).unwrap();

    vector_db.unwrap().save_collection("vectors", &collection).unwrap();
}

// Delete Collection
pub fn delete_collection() {
    let vector_db = connect_db();
    vector_db.unwrap().delete_collection("vectors").unwrap();
}

// Get Vector Database path
fn get_db_path() -> String {
    let mut db_path = ".buddhi-ai/db/";
    match home_dir() {
        Some(mut home_path) => {
            home_path.push(".buddhi-ai/db/");
            db_path = Box::leak(home_path.to_str().unwrap().to_string().into_boxed_str());

            println!("Path for a config file: {:?}", db_path);
        }
        None => {
            eprintln!("Could not determine user's home directory.");
        }
    }
    db_path.to_string()
}
